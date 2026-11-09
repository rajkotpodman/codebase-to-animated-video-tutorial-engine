import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Codebase-to-Video Engine | Studio",
  description: "Transform public GitHub repositories into animated video architecture tutorials using Repomix, Gemini, Manim, and Neural TTS.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className="min-h-screen bg-background font-sans text-foreground"
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  );
}

