import { ScrollReveal } from "@/components/effects/scroll-reveal";

export function CTA() {
  return (
    <section className="py-32 bg-surface text-center historical-texture relative border-t border-outline-variant/10">
      <div className="container mx-auto px-6 relative z-10">
        <ScrollReveal>
          <h2 className="text-5xl md:text-7xl font-headline font-black mb-8 uppercase tracking-tighter">
            History Awaits <br />
            Your <span className="text-primary italic">Command</span>
          </h2>
        </ScrollReveal>
        <ScrollReveal delay={150}>
          <p className="text-on-surface-variant font-body max-w-2xl mx-auto mb-12 uppercase tracking-widest text-xs">
            Are you ready to rule through the shell?
          </p>
        </ScrollReveal>
        <ScrollReveal delay={300}>
          <div className="inline-flex flex-col sm:flex-row gap-6">
            <button className="bg-primary text-on-primary px-12 py-5 font-label font-bold uppercase tracking-widest hover:scale-105 transition-transform active:scale-[0.98]">
              Establish Empire
            </button>
            <button className="bg-surface-container-high text-on-surface px-12 py-5 font-label font-bold uppercase tracking-widest border border-outline-variant/20 hover:border-primary transition-colors">
              Read the Wiki
            </button>
          </div>
        </ScrollReveal>
      </div>
      <div className="absolute bottom-0 left-0 w-full h-1/2 bg-gradient-to-t from-background to-transparent opacity-50" />
    </section>
  );
}
