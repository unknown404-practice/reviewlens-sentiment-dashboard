import "./globals.css";

export const metadata = {
  title: "ReviewLens | E-Commerce Review Sentiment Intelligence",
  description: "Executive analytics dashboard for e-commerce reviews powered by FastAPI, VADER NLP, and Next.js.",
  applicationName: "ReviewLens",
  keywords: ["sentiment analysis", "review intelligence", "VADER NLP", "FastAPI", "Next.js", "e-commerce analytics"],
  authors: [{ name: "ReviewLens Team" }],
  creator: "ReviewLens",
  metadataBase: new URL("http://localhost:3000"),
  openGraph: {
    title: "ReviewLens | E-Commerce Review Sentiment Intelligence",
    description: "Production-ready sentiment analytics for e-commerce customer feedback.",
    type: "website",
    siteName: "ReviewLens",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: "#080c14",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          rel="icon"
          href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🔍</text></svg>"
        />
      </head>
      <body className="bg-background text-slate-100 min-h-screen antialiased selection:bg-brand-primary/20 selection:text-brand-primary">
        <div className="relative min-h-screen flex flex-col">
          {children}
        </div>
      </body>
    </html>
  );
}
