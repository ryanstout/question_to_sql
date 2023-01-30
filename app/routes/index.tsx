import { redirect } from "@remix-run/server-runtime"

export const loader: LoaderFunction = async ({ request }) => {
  return redirect("/admin/1/chart/raw")
}
