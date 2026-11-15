import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";
import { BackendWarmer } from "@/components/layout/BackendWarmer";

export const metadata: Metadata = {
  title: "BrandSentinel — Intelligent Brand Governance Platform",
  description: "Enterprise pre-publication content review and brand compliance gate",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased min-h-screen">
        <BackendWarmer />
        <AuthProvider>
          <Navbar />
          <div className="flex">
            <Sidebar />
            <main className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full">
              {children}
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
