import { useEffect, useState } from "react";

type HeaderProps = {
  loginHref: string;
  registerHref: string;
  landingHref: string;
  aboutusHref: string;
};



export function Header({ loginHref, registerHref, landingHref, aboutusHref }: HeaderProps) {
    const navLinks = [
      { name: "Home", href: landingHref },
      { name: "About Us", href: aboutusHref },
      // add more links as needed
    ];
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [active, setActive] = useState("#");
  const onDarkHero = !scrolled;

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const updateActive = () => setActive(window.location.hash || "#");
    updateActive();
    window.addEventListener("hashchange", updateActive);
    return () => window.removeEventListener("hashchange", updateActive);
  }, []);

  return (
    <header
      className={`sticky top-0 z-50 w-full transition ${
        scrolled
          ? "border-b border-clay-500/20 bg-sand-100/80 shadow-sm backdrop-blur"
          : "bg-transparent"
      }`}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <a
          href={landingHref}
          className={`font-display text-2xl italic transition ${
            onDarkHero ? "text-white" : "text-espresso-900"
          }`}
        >
          Chillazi
        </a>

        <nav className="hidden items-center gap-8 text-md font-medium md:flex">
          {navLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              className={`relative py-1 transition ${
                active === link.href
                  ? onDarkHero
                    ? "text-sand-50 after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-full after:rounded-full after:bg-sand-200"
                    : "text-clay-600 after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-full after:rounded-full after:bg-clay-500"
                  : onDarkHero
                    ? "text-white/78 hover:text-white"
                    : "text-espresso-900/80 hover:text-clay-600"
              }`}
            >
              {link.name}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-3">
         

          {registerHref && (
            <a
              href={registerHref}
              className="hidden items-center rounded-full bg-clay-600 px-4 py-2 text-sm font-medium text-white shadow-md shadow-clay-500/20 transition hover:bg-clay-700 md:inline-flex"
            >
              Get started
            </a>
          )}

          <button
            className="flex flex-col gap-1.5 md:hidden"
            onClick={() => setOpen((currentOpen) => !currentOpen)}
            aria-expanded={open}
            aria-label={open ? "Close navigation menu" : "Open navigation menu"}
          >
            <span
              className={`h-0.5 w-6 transition ${
                onDarkHero ? "bg-white" : "bg-espresso-900"
              } ${open ? "translate-y-2 rotate-45" : ""}`}
            />
            <span
              className={`h-0.5 w-6 transition ${
                onDarkHero ? "bg-white" : "bg-espresso-900"
              } ${open ? "opacity-0" : ""}`}
            />
            <span
              className={`h-0.5 w-6 transition ${
                onDarkHero ? "bg-white" : "bg-espresso-900"
              } ${open ? "-translate-y-2 -rotate-45" : ""}`}
            />
          </button>
        </div>
      </div>

      {open && (
        <div
          className={`space-y-4 border-t px-6 pb-4 md:hidden ${
            onDarkHero
              ? "border-white/10 bg-[rgba(7,11,20,0.94)] text-white backdrop-blur"
              : "border-clay-500/20 bg-sand-100"
          }`}
        >
          {navLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              onClick={() => setOpen(false)}
              className={`block text-sm font-medium ${
                active === link.href
                  ? onDarkHero
                    ? "text-sand-50"
                    : "text-clay-600"
                  : onDarkHero
                    ? "text-white/78 hover:text-white"
                    : "text-espresso-900/80 hover:text-clay-600"
              }`}
            >
              {link.name}
            </a>
          ))}
          <a
            href={loginHref}
            className={`block rounded-full border px-4 py-2 text-center text-sm font-medium transition ${
              onDarkHero
                ? "border-white/20 text-white hover:bg-white/10"
                : "border-clay-500/30 text-espresso-900 hover:bg-clay-500/10"
            }`}
          >
            Log in
          </a>
          {registerHref && (
            <a
              href={registerHref}
              className="block rounded-full bg-clay-600 px-4 py-2 text-center text-sm font-medium text-white shadow-sm transition hover:bg-clay-700"
            >
              Get started
            </a>
          )}
        </div>
      )}
    </header>
  );
}
