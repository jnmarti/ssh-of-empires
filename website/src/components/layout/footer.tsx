export function Footer() {
  return (
    <footer className="bg-surface-container-low border-t border-outline-variant/10 py-12 px-8 w-full">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-7xl mx-auto">
        <div>
          <div className="text-lg font-bold text-primary mb-4 uppercase font-headline">
            SSH of Empires
          </div>
          <p className="text-outline-variant font-body text-xs uppercase tracking-widest leading-relaxed">
            The ultimate terminal-based historical strategy experience.
            <br />
            Crafted for the elite strategist.
          </p>
        </div>

        <div className="flex flex-col gap-4">
          <h6 className="text-primary font-label text-[10px] uppercase tracking-[0.3em] mb-2">
            Network
          </h6>
          <div className="flex flex-col gap-2">
            <a
              className="text-outline-variant hover:text-primary font-body text-xs uppercase tracking-widest transition-all"
              href="#"
            >
              &gt; Twitter
            </a>
            <a
              className="text-outline-variant hover:text-primary font-body text-xs uppercase tracking-widest transition-all"
              href="#"
            >
              &gt; GitHub
            </a>
            <a
              className="text-outline-variant hover:text-primary font-body text-xs uppercase tracking-widest transition-all"
              href="#"
            >
              &gt; Discord
            </a>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <h6 className="text-primary font-label text-[10px] uppercase tracking-[0.3em] mb-2">
            Legal
          </h6>
          <div className="flex flex-col gap-2">
            <a
              className="text-outline-variant hover:text-primary font-body text-xs uppercase tracking-widest transition-all"
              href="#"
            >
              &gt; Terms of Service
            </a>
            <p className="text-outline-variant font-body text-[10px] mt-4 opacity-50">
              &copy; 1066-2024 EMPIRE_OS TERMINAL COMMAND. ALL RIGHTS RESERVED.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
