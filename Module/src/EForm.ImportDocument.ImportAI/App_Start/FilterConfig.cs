using System.Web;
using System.Web.Mvc;

namespace EForm.ImportDocument.ImportAI
{
	public class FilterConfig
	{
		public static void RegisterGlobalFilters(GlobalFilterCollection filters)
		{
			filters.Add(new HandleErrorAttribute());
		}
	}
}
