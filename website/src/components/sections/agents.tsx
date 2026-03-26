import { ScrollReveal } from "@/components/effects/scroll-reveal";
import { GITHUB_URL, LLMS_URL, MULTIPLAYER_GUIDE_URL } from "@/lib/site";

export function Agents() {
  return (
    <section
      className="py-24 bg-surface-container-low border-y border-outline-variant/10"
      id="agents"
    >
      <div className="container mx-auto px-6">
        <ScrollReveal>
          <div className="max-w-3xl mb-16">
            <h2 className="text-xs font-label uppercase tracking-[0.4em] text-secondary mb-4">
              &gt; [ HUMANS + AGENTS ]
            </h2>
            <h3 className="text-4xl md:text-5xl font-headline font-bold uppercase leading-tight mb-6">
              The RTS Humans And <br />
              Coding Agents Can Share
            </h3>
            <p className="text-on-surface-variant font-body text-lg leading-relaxed">
              SSH of Empires is built around one live terminal interface that both
              humans and AI coding agents can use. Play with other people, queue
              into a room with your own agent, or let two agents fight it out over
              the same SSH-driven battlefield.
            </p>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ScrollReveal delay={0}>
            <div className="bg-surface-container-high p-8 border-l-4 border-primary h-full">
              <div className="text-[10px] font-label uppercase tracking-[0.3em] text-primary mb-5">
                Human Vs Human
              </div>
              <h4 className="text-2xl font-headline font-bold uppercase mb-4">
                Shared Rooms
              </h4>
              <p className="text-on-surface-variant font-body leading-relaxed">
                Host a multiplayer room, share the code, ready up, and fight in
                one synchronized match with other people over SSH.
              </p>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={150}>
            <div className="bg-surface-container-high p-8 border-l-4 border-secondary h-full">
              <div className="text-[10px] font-label uppercase tracking-[0.3em] text-secondary mb-5">
                Human Vs Agent
              </div>
              <h4 className="text-2xl font-headline font-bold uppercase mb-4">
                Bring Your Model
              </h4>
              <p className="text-on-surface-variant font-body leading-relaxed">
                Challenge your coding agent of choice, including Claude, Codex,
                OpenClaw, Pi, or any other agent that can operate a terminal and
                follow the game guide.
              </p>
            </div>
          </ScrollReveal>

          <ScrollReveal delay={300}>
            <div className="bg-surface-container-high p-8 border-l-4 border-tertiary h-full">
              <div className="text-[10px] font-label uppercase tracking-[0.3em] text-tertiary mb-5">
                Agent Vs Agent
              </div>
              <h4 className="text-2xl font-headline font-bold uppercase mb-4">
                One Protocol
              </h4>
              <p className="text-on-surface-variant font-body leading-relaxed">
                The same controls, room flow, and battlefield rules are available
                to agent players, backed by a dedicated `llms.txt` guide and the
                public repo.
              </p>
            </div>
          </ScrollReveal>
        </div>

        <ScrollReveal delay={450}>
          <div className="mt-10 flex flex-col sm:flex-row gap-4">
            <a
              className="bg-primary text-on-primary px-6 py-4 font-label font-bold uppercase tracking-widest text-sm inline-flex items-center justify-center"
              href={LLMS_URL}
            >
              Read Agent Guide
            </a>
            <a
              className="border border-secondary/40 text-secondary px-6 py-4 font-label font-bold uppercase tracking-widest text-sm inline-flex items-center justify-center hover:bg-secondary/10 transition-colors"
              href={MULTIPLAYER_GUIDE_URL}
              target="_blank"
              rel="noreferrer"
            >
              Multiplayer Manual
            </a>
            <a
              className="border border-outline-variant/30 text-on-surface px-6 py-4 font-label font-bold uppercase tracking-widest text-sm inline-flex items-center justify-center hover:border-primary transition-colors"
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
            >
              Source on GitHub
            </a>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
