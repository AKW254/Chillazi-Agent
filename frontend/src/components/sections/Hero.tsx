type HeroProps = {
  registerHref: string;
};

export function Hero({ registerHref }: HeroProps) {
  return (
    <section className="relative flex min-h-[90vh] items-center justify-center overflow-hidden px-6">
      <div
        aria-hidden="true"
        className="absolute inset-x-0 top-1/2 h-72 -translate-y-1/2 bg-[radial-gradient(circle,rgba(203,95,49,0.26),transparent_60%)] blur-3xl"
      />

      <div className="relative mx-auto max-w-4xl space-y-6 text-center animate-[fade-up_0.7s_ease_both]">
        <p className="text-sm font-medium uppercase tracking-[0.32em] text-sand-200/80">
          Chillazi online chatbot 
        </p>

        <h1 className="font-display text-5xl leading-tight italic text-sand-50 sm:text-6xl md:text-7xl">
          True AI assistant for your <br />
          <br />
          <span className="text-clay-500">online business</span>
        </h1>

        <p className="mx-auto max-w-2xl text-base leading-8 text-white/72 sm:text-lg">
          Build your own AI assistant to handle customer inquiries, automate support, and boost engagement. Get started in minutes with our easy-to-use chatbot.
          Try it out and see how it can transform your online business today! 
        </p>

        <div className="flex flex-col justify-center gap-4 pt-4 sm:flex-row">
          <a
            href={registerHref}
            className="inline-block rounded-full bg-clay-600 px-8 py-3 font-medium text-white shadow-lg shadow-clay-500/20 transition hover:bg-clay-700"
          >
            Get started
          </a>
        </div>
      </div>
    </section>
  );
}
