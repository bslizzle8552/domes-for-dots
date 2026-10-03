import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Domes World Creator Lab",
  description: "A private generated Dot world with durable simulated life and protected revisions.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}

