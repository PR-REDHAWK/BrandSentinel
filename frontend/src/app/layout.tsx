import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";

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
        <AuthProvider>
          <Navbar />
          <div className="flex">
            <Sidebar />
            <main className="flex-1 p-8 overflow-y-auto max-w-7xl mx-auto">
              {children}
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
