import '../index.css';

export const metadata = {
  title: 'Orian',
  description: 'Orian AI - Advanced Digital Brain & Orchestrator',
  icons: {
    icon: '/favicon.svg',
  },
};

export const viewport = {
  themeColor: '#030712',
  width: 'device-width',
  initialScale: 1.0,
  maximumScale: 1.0,
  userScalable: false,
  viewportFit: 'cover',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700;900&family=Outfit:wght@300;400;700;900&family=Roboto+Mono:wght@400;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-[#010208] text-slate-100 overflow-hidden antialiased select-none">
        {children}
      </body>
    </html>
  );
}
