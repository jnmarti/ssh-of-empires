import type { Metadata } from "next";
import { Noto_Serif, Space_Grotesk } from "next/font/google";
import "./globals.css";

const notoSerif = Noto_Serif({
  variable: "--font-noto-serif",
  subsets: ["latin"],
  weight: ["400", "700", "900"],
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "SSH of Empires — Conquer The Terminal",
  description:
    "Experience history through the cold precision of the command line. A massive RTS where strategy is written in code and empires are built one command at a time.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${notoSerif.variable} ${spaceGrotesk.variable} dark`}
    >
      <body className="min-h-screen bg-background text-on-surface">
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          precedence="default"
        />
        {children}
      </body>
    </html>
  );
}
