using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Security.Cryptography;
using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Application;

namespace EForm.ImportDocument.Infrastructure
{
    public sealed class SecureImportFileStorage : IImportFileStorage
    {
        private static readonly string[] Allowed = { ".xlsx", ".xlsm" };
        private readonly string _root;
        private readonly long _maxFileBytes;
        private readonly long _maxUncompressedBytes;
        private readonly int _maxZipRatio;

        public SecureImportFileStorage(string root, long maxFileBytes = 25 * 1024 * 1024,
            long maxUncompressedBytes = 200 * 1024 * 1024, int maxZipRatio = 100)
        {
            if (string.IsNullOrWhiteSpace(root)) throw new ArgumentNullException("root");
            _root = Path.GetFullPath(root);
            _maxFileBytes = maxFileBytes;
            _maxUncompressedBytes = maxUncompressedBytes;
            _maxZipRatio = maxZipRatio;
            Directory.CreateDirectory(_root);
        }

        public async Task<StoredImportFile> SaveAsync(Stream input, string originalName, CancellationToken cancellationToken)
        {
            if (input == null || !input.CanRead) throw new ImportValidationException("Luồng tệp không đọc được.");
            var safeName = Path.GetFileName(originalName ?? string.Empty);
            var extension = Path.GetExtension(safeName).ToLowerInvariant();
            if (!Allowed.Contains(extension)) throw new ImportValidationException("Chỉ hỗ trợ .xlsx và .xlsm.");
            var finalPath = Path.Combine(_root, Guid.NewGuid().ToString("N") + extension);
            var tempPath = finalPath + ".uploading";
            try
            {
                long count = 0;
                using (var output = new FileStream(tempPath, FileMode.CreateNew, FileAccess.Write, FileShare.None, 81920, true))
                {
                    var buffer = new byte[81920];
                    int read;
                    while ((read = await input.ReadAsync(buffer, 0, buffer.Length, cancellationToken).ConfigureAwait(false)) > 0)
                    {
                        count += read;
                        if (count > _maxFileBytes) throw new ImportValidationException("Tệp vượt giới hạn dung lượng.");
                        await output.WriteAsync(buffer, 0, read, cancellationToken).ConfigureAwait(false);
                    }
                }
                ValidatePackage(tempPath);
                string hash;
                using (var sha = SHA256.Create())
                using (var file = File.OpenRead(tempPath))
                    hash = BitConverter.ToString(sha.ComputeHash(file)).Replace("-", string.Empty).ToLowerInvariant();
                File.Move(tempPath, finalPath);
                return new StoredImportFile { OriginalName = safeName, FullPath = finalPath, Sha256 = hash, Size = count };
            }
            catch
            {
                if (File.Exists(tempPath)) File.Delete(tempPath);
                throw;
            }
        }

        public Task DeleteAsync(string fullPath, CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (string.IsNullOrWhiteSpace(fullPath)) return Task.CompletedTask;
            var resolved = Path.GetFullPath(fullPath);
            var prefix = _root.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
            if (!resolved.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("Từ chối xóa tệp ngoài thư mục import.");
            if (File.Exists(resolved)) File.Delete(resolved);
            return Task.CompletedTask;
        }

        private void ValidatePackage(string path)
        {
            using (var input = File.OpenRead(path))
            {
                var signature = new byte[4];
                if (input.Read(signature, 0, 4) != 4 || signature[0] != 0x50 || signature[1] != 0x4b || signature[2] != 0x03 || signature[3] != 0x04)
                    throw new ImportValidationException("Chữ ký tệp không phải Office Open XML.");
            }
            long total = 0;
            using (var archive = ZipFile.OpenRead(path))
            {
                foreach (var entry in archive.Entries)
                {
                    total += entry.Length;
                    if (total > _maxUncompressedBytes) throw new ImportValidationException("Dung lượng giải nén vượt giới hạn.");
                    if (entry.CompressedLength == 0 && entry.Length > 0) throw new ImportValidationException("ZIP entry bất thường.");
                    if (entry.CompressedLength > 0 && entry.Length / entry.CompressedLength > _maxZipRatio)
                        throw new ImportValidationException("Tỷ lệ nén bất thường.");
                }
            }
        }
    }
}

