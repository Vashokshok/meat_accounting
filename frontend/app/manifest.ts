import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Учёт мяса",
    short_name: "Мясо",
    start_url: "/",
    display: "standalone",
    background_color: "#121212",
    theme_color: "#121212",
    icons: [
      { src: "/static/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/static/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
