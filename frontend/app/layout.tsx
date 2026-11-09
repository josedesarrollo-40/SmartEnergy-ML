import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

import { Sidebar } from "@/components/sidebar";

export const metadata: Metadata = {
  title: "SmartEnergy ML",
  description:
    "Plataforma de análisis y predicción del consumo eléctrico residencial.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full">
        <div className="flex min-h-screen flex-col md:flex-row md:items-start">
          <Sidebar />
          <main className="w-full min-w-0 flex-1 overflow-x-hidden p-4 sm:p-6 md:p-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
