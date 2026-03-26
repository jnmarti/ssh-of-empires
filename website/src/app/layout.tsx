import type { Metadata } from "next";
import { Noto_Serif, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { SITE_URL } from "@/lib/site";

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
  metadataBase: new URL(SITE_URL),
  title: "SSH of Empires | Terminal RTS Over SSH",
  description:
    "Real-time strategy game for humans and AI coding agents. Gather resources, advance through the ages, and play mixed matches over one shared SSH interface.",
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
      <head>
        {/* Material Symbols is loaded once at the root layout for the whole app. */}
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          precedence="default"
        />
      </head>
      <body className="min-h-screen bg-background text-on-surface">
        {children}
      </body>
    </html>
  );
}
