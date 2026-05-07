import { Header } from "../components/layout/Header";
import { Hero } from "../components/sections/Hero";
import { Footer } from "../components/layout/Footer";



type Props = {
  landingHref: string;
  aboutusHref: string;
  loginHref: string;
  registerHref: string;
};

export function LandingPage({ landingHref, aboutusHref, loginHref, registerHref }: Props) {
  return (
    <main className="min-h-screen flex flex-col bg-gradient-to-br from-[#0b1220] via-[#111827] to-[#020617] text-white">
      {/* Header stays centered */}
      <Header loginHref={loginHref} registerHref={registerHref} landingHref={landingHref} aboutusHref={aboutusHref} />

      {/* Content area */}
      <div className="flex-1">
        <Hero registerHref={registerHref} />
      </div>

      {/* Footer sticks to bottom */}
      <Footer company="Chillazi" />
    </main>
  );
}
