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
    public sealed class SecureWorkbookStorage : IWorkbookStorage
    {
        private readonly string _root;
        private readonly long _maxBytes;
        public SecureWorkbookStorage(string root, long maxBytes = 25 * 1024 * 1024)
        {
            if (string.IsNullOrWhiteSpace(root)) throw new ArgumentNullException("root");
            _root = Path.GetFullPath(root);
            _maxBytes = maxBytes;
            Directory.CreateDirectory(_root);
        }

        public async Task<StoredWorkbook> SaveAsync(Stream stream, string originalName, CancellationToken cancellationToken)
        {
            if (stream == null || !stream.CanRead) throw new ImportRequestException("File không đọc được.");
            var safeName = Path.GetFileName(originalName ?? string.Empty);
            var extension = Path.GetExtension(safeName).ToLowerInvariant();
            if (extension != ".xlsx" && extension != ".xlsm") throw new ImportRequestException("Chỉ hỗ trợ .xlsx/.xlsm.");
            var path = Path.Combine(_root, Guid.NewGuid().ToString("N") + extension);
            var temporary = path + ".uploading";
            try
            {
                long size = 0;
                using (var output = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None, 81920, true))
                {
                    var buffer = new byte[81920];
                    int read;
                    while ((read = await stream.ReadAsync(buffer, 0, buffer.Length, cancellationToken).ConfigureAwait(false)) > 0)
                    {
                        size += read;
                        if (size > _maxBytes) throw new ImportRequestException("File vượt giới hạn 25 MiB.");
                        await output.WriteAsync(buffer, 0, read, cancellationToken).ConfigureAwait(false);
                    }
                }
                ValidateOfficePackage(temporary);
                string hash;
                using (var sha = SHA256.Create())
                using (var input = File.OpenRead(temporary))
                    hash = BitConverter.ToString(sha.ComputeHash(input)).Replace("-", string.Empty).ToLowerInvariant();
                File.Move(temporary, path);
                return new StoredWorkbook { FullPath = path, OriginalName = safeName, Sha256 = hash, Size = size };
            }
            catch
            {
                if (File.Exists(temporary)) File.Delete(temporary);
                throw;
            }
        }

        public Task DeleteAsync(string fullPath, CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var resolved = Path.GetFullPath(fullPath ?? string.Empty);
            var prefix = _root.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
            if (!resolved.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)) throw new InvalidOperationException("File ngoài upload root.");
            if (File.Exists(resolved)) File.Delete(resolved);
            return Task.CompletedTask;
        }

        private static void ValidateOfficePackage(string path)
        {
            using (var input = File.OpenRead(path))
            {
                var signature = new byte[4];
                if (input.Read(signature, 0, 4) != 4 || signature[0] != 0x50 || signature[1] != 0x4b || signature[2] != 0x03 || signature[3] != 0x04)
                    throw new ImportRequestException("File không phải Office Open XML.");
            }
            using (var archive = ZipFile.OpenRead(path))
            {
                if (archive.GetEntry("[Content_Types].xml") == null || archive.GetEntry("xl/workbook.xml") == null)
                    throw new ImportRequestException("Gói ZIP không phải workbook Excel hợp lệ.");
            }
        }
    }
}
