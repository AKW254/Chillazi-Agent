import { Header } from "../components/layout/Header";
import { AboutCard } from "../components/sections/AboutCard";
import aboutImage from "../assets/About us.png";
import { Footer } from "../components/layout/Footer";



type Props = {
  landingHref: string;
  aboutusHref: string;
  loginHref: string;
  registerHref: string;
};

export function AboutUsPage({ landingHref, aboutusHref, loginHref, registerHref }: Props) {
  return (
    <main className="min-h-screen flex flex-col bg-gradient-to-br from-[#0b1220] via-[#111827] to-[#020617] text-white">
      {/* Header stays centered */}
      <Header
        loginHref={loginHref}
        registerHref={registerHref}
        landingHref={landingHref}
        aboutusHref={aboutusHref}
      />

      <section id="about" className="py-6 px-6 max-w-10xl mx-auto">
        <AboutCard
          imageSrc={aboutImage}
          imageAlt="Team working together"
          title="About Chillazi"
          imagePosition="left"
        >
          <p>
            We’re a small team of data lovers who think every online business
            should have access to powerful analytics – without the complexity.
          </p>
          <p>
            Chillazi connects to your tools in minutes and turns raw data into
            clear, actionable insights.
          </p>
        </AboutCard>
      </section>
      {/* Footer sticks to bottom */}
      <Footer company="Chillazi" />
    </main>
  );
}
