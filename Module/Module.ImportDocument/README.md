# Module.ImportDocument — backend Web API tối giản

ASP.NET Web API 2 trên .NET Framework 4.8, chia thành bốn project: `Domain`, `Application`, `Infrastructure`, `ImportApi`.

`Application/ImportPipelineService` thực hiện đúng một use case: kiểm tra request/quyền → lưu file tạm → gọi AI `/parse` → trả JSON → dọn file. `ImportApi/ImportController` public duy nhất `POST /api/import/parse`.

## Build

```powershell
dotnet build .\eform_btp.slnx -c Release
```

NuGet: `Microsoft.AspNet.WebApi.Core`, `Microsoft.AspNet.WebApi.WebHost`, `Swashbuckle.Core`, `MySql.Data`.

## Host eForm

```csharp
var permission = new EFormImportPermission(new ExistingEFormPermissionPort());
var storage = new SecureWorkbookStorage(@"D:\eform-import\uploads");
var ai = new AiParseHttpClient(new HttpClient(), new Uri("http://127.0.0.1:8010/"));
ImportApiRuntime.Configure(new ImportPipelineService(permission, storage, ai));
Global.asax/Application_Start tự động gọi `GlobalConfiguration.Configure(App_Start.WebApiConfig.Register)`.
```

`ExistingEFormPermissionPort` phải gọi `DocumentPermissions.SuaVanBan` và `TaskReportPeriod.IsLock` thật. Controller lấy user từ `ClaimsPrincipal`, không nhận user ID từ FE. Swagger UI: `/swagger/ui/index`.

## MySQL

Chạy [`Database/001_minimal_import.sql`](Database/001_minimal_import.sql) sau backup/staging review. Chỉ lưu audit metadata/dictionary; không lưu raw cell/workbook. `MySqlConnectionFactory` nhận connection string từ protected configuration.
