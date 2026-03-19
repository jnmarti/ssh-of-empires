import { ScrollReveal } from "@/components/effects/scroll-reveal";

export function Concept() {
  return (
    <section className="py-24 bg-surface">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
          <div>
            <ScrollReveal>
              <h2 className="text-xs font-label uppercase tracking-[0.4em] text-primary-container mb-4">
                &gt; [ ARCHITECTURE ]
              </h2>
              <h3 className="text-4xl md:text-5xl font-headline font-bold mb-8 uppercase leading-tight">
                The Strategy is <br />
                In The Syntax
              </h3>
            </ScrollReveal>
            <ScrollReveal delay={150}>
              <div className="space-y-6 text-on-surface-variant font-body text-lg leading-relaxed">
                <p>
                  SSH of Empires strips away the distractions of modern graphics
                  to focus on the core of strategy:{" "}
                  <span className="text-on-surface font-bold">
                    Intelligence, Speed, and Execution.
                  </span>
                </p>
                <p>
                  Every villager assigned, every unit trained, and every wall built
                  is a command sent directly to the core engine. You are not just a
                  player; you are the system operator of a rising civilization.
                </p>
              </div>
            </ScrollReveal>
            <ScrollReveal delay={300}>
              <div className="mt-12 grid grid-cols-2 gap-8">
                <div className="border-t border-outline-variant/20 pt-4">
                  <span className="text-3xl font-headline text-primary block mb-2">
                    0.0ms
                  </span>
                  <span className="text-[10px] font-label uppercase tracking-widest text-on-surface-variant leading-none">
                    Input Latency
                  </span>
                </div>
                <div className="border-t border-outline-variant/20 pt-4">
                  <span className="text-3xl font-headline text-primary block mb-2">
                    100%
                  </span>
                  <span className="text-[10px] font-label uppercase tracking-widest text-on-surface-variant leading-none">
                    Scriptable UI
                  </span>
                </div>
              </div>
            </ScrollReveal>
          </div>

          <ScrollReveal direction="right" delay={200}>
            <div className="relative">
              <div className="bg-surface-container-lowest border border-outline-variant/20 p-2 shadow-2xl">
                <div className="bg-surface-container-low p-4 flex items-center justify-between border-b border-outline-variant/20">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 bg-error rounded-full" />
                    <div className="w-2 h-2 bg-tertiary rounded-full" />
                    <div className="w-2 h-2 bg-secondary rounded-full" />
                  </div>
                  <span className="text-[10px] font-label text-on-surface-variant uppercase tracking-widest">
                    MAP_RENDER_01.EXE
                  </span>
                </div>
                <div className="p-6 aspect-square overflow-hidden bg-black flex items-center justify-center">
                  <pre className="text-[8px] leading-[1.1] text-secondary font-mono whitespace-pre">
                    {`                ~~~~~~~~~~~~~~~~~~~~~~~
                ~~~~~~~~~~~~  ... ~~~~~~~
               ~~~~~~~~~~   .::::.  ~~~~~
               ~~~~~~     .::::::::.  ~~~~
               ~~~~      ::::::::::::  ~~~
               ~~~      ::::::::::::::  ~~
               ~~~      ::::::::::::::  ~~
               ~~~      ::::::::::::::  ~~
               ~~~~      ::::::::::::  ~~~
               ~~~~~~     ::::::::::  ~~~~
               ~~~~~~~~~   '::::::'  ~~~~~
               ~~~~~~~~~~~~  '::'  ~~~~~~~
                ~~~~~~~~~~~~~~~~~~~~~~~
                 [ CASTLE_FOUNDATION ]`}
                  </pre>
                </div>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
}
