type FooterProps = {
  company?: string;
  year?: number;
};

export function Footer({
  company = "Your Company, Inc.",
  year = new Date().getFullYear(),
}: FooterProps) {
  return (
    <footer className="mt-20 border-t border-white/10 bg-[#0b1220]">
      <div className="max-w-6xl mx-auto px-6 py-6 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* LEFT */}
        <p className="text-sm text-gray-400">
          © {year} {company}. All rights reserved.
        </p>

        {/* RIGHT (SOCIALS) */}
        <div className="flex items-center gap-5 text-gray-400">
          <a href="#" className="hover:text-white transition">
            {/* Facebook */}
            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
              <path d="M22 12a10 10 0 10-11.5 9.9v-7h-2.7v-2.9h2.7V9.8c0-2.7 1.6-4.2 4-4.2 1.2 0 2.4.2 2.4.2v2.6h-1.3c-1.3 0-1.7.8-1.7 1.6v1.9h2.9l-.5 2.9h-2.4v7A10 10 0 0022 12z" />
            </svg>
          </a>

          <a href="#" className="hover:text-white transition">
            {/* Instagram */}
            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
              <path d="M7 2C4.8 2 3 3.8 3 6v12c0 2.2 1.8 4 4 4h10c2.2 0 4-1.8 4-4V6c0-2.2-1.8-4-4-4H7zm5 5a5 5 0 110 10 5 5 0 010-10zm6.5-.9a1.1 1.1 0 11-2.2 0 1.1 1.1 0 012.2 0z" />
            </svg>
          </a>

          <a href="#" className="hover:text-white transition">
            {/* X / Twitter */}
            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
              <path d="M18 2h3l-7 8 8 12h-6l-5-7-6 7H2l8-9L2 2h6l4 6 6-6z" />
            </svg>
          </a>

          <a href="#" className="hover:text-white transition">
            {/* GitHub */}
            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
              <path d="M12 .5A12 12 0 000 12.7c0 5.4 3.4 10 8.2 11.6.6.1.8-.3.8-.6v-2.2c-3.3.7-4-1.6-4-1.6-.5-1.3-1.2-1.6-1.2-1.6-1-.7.1-.7.1-.7 1.1.1 1.7 1.2 1.7 1.2 1 .1.8 1.6 2.7 1.2.1-.7.4-1.2.7-1.5-2.7-.3-5.6-1.4-5.6-6.3 0-1.4.5-2.6 1.2-3.5-.1-.3-.5-1.6.1-3.3 0 0 1-.3 3.4 1.3a11.5 11.5 0 016.2 0c2.4-1.6 3.4-1.3 3.4-1.3.6 1.7.2 3 .1 3.3.8.9 1.2 2.1 1.2 3.5 0 4.9-3 6-5.7 6.3.4.4.8 1 .8 2.1v3.1c0 .3.2.7.8.6A12 12 0 0024 12.7 12 12 0 0012 .5z" />
            </svg>
          </a>

          <a href="#" className="hover:text-white transition">
            {/* YouTube */}
            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
              <path d="M23.5 6.2a3 3 0 00-2.1-2.1C19.6 3.5 12 3.5 12 3.5s-7.6 0-9.4.6A3 3 0 00.5 6.2 31.5 31.5 0 000 12a31.5 31.5 0 00.5 5.8 3 3 0 002.1 2.1c1.8.6 9.4.6 9.4.6s7.6 0 9.4-.6a3 3 0 002.1-2.1A31.5 31.5 0 0024 12a31.5 31.5 0 00-.5-5.8zM9.8 15.5v-7l6 3.5-6 3.5z" />
            </svg>
          </a>
        </div>
      </div>
    </footer>
  );
}
