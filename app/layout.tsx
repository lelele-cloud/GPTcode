import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Pictionary",
  description: "Draw on the canvas and let AI guess your doodle."
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
