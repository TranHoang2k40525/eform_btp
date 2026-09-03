# Kiến trúc backend tối giản

```text
Module.ImportDocument/
├── Domain/          Module.ImportDocument.Domain.csproj
├── Application/     Module.ImportDocument.Application.csproj
├── Infrastructure/  Module.ImportDocument.Infrastructure.csproj
└── ImportApi/       Module.ImportDocument.ImportApi.csproj (Web API 2 + Swagger)
```

`Domain` chỉ chứa model request/schema/result, không phụ thuộc Web API hay DB. `Application/ImportPipelineService` là use case duy nhất: kiểm schema → permission/lock → lưu file tạm → gọi AI → dọn file → trả result. `Infrastructure` chứa storage an toàn, HTTP client AI, adapter permission eForm và MySQL factory. `ImportApi` chứa controller một route, config route và Swagger.

## Composition root eForm

```csharp
var permission = new EFormImportPermission(new ExistingEFormPermissionPort());
var storage = new SecureWorkbookStorage(@"D:\eform-import\uploads");
var ai = new AiParseHttpClient(new HttpClient(), new Uri("http://127.0.0.1:8010/"));
ImportApiRuntime.Configure(new ImportPipelineService(permission, storage, ai));
GlobalConfiguration.Configure(WebApiConfig.Register);
```

`ExistingEFormPermissionPort` phải gọi `DocumentPermissions.SuaVanBan` và `TaskReportPeriod.IsLock` thật. Controller lấy `ClaimsPrincipal`; không tin user ID FE. Endpoint trả JSON bóc tách để FE preview, không cho AI ghi `DocumentContent` trực tiếp.

Không còn public job/analyze/map/validate/confirm/commit API riêng lẻ vì không cần cho use case hiện tại. `ImportAudit`/dictionary là persistence tối thiểu tùy chọn, không lưu raw cells.

Đây là ASP.NET Web API 2 trên .NET Framework 4.8, không phải ASP.NET Core. Package: `Microsoft.AspNet.WebApi.Core`, `Microsoft.AspNet.WebApi.WebHost`, `Swashbuckle.Core`, `MySql.Data`.

