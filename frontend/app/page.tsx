import { redirect } from "next/navigation";

/** La pantalla informativa vive en `/inicio`; la raíz lleva al contenido. */
export default function HomePage() {
  redirect("/dashboards");
}
