using System.Web.Mvc;
namespace EForm.ImportDocument.ImportApi.Controllers
{
    public class HomeController : Controller
    {
        [HttpGet]
        public ActionResult Index()
        {
            return View();
        }
    }
}
