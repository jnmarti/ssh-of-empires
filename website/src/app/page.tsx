import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { Hero } from "@/components/sections/hero";
import { Agents } from "@/components/sections/agents";
import { Concept } from "@/components/sections/concept";
import { Connect } from "@/components/sections/connect";
import { GameModes } from "@/components/sections/game-modes";
import { Civilizations } from "@/components/sections/civilizations";
import { CTA } from "@/components/sections/cta";

export default function Home() {
  return (
    <>
      <Header />
      <main className="pt-16">
        <Hero />
        <Agents />
        <Concept />
        <Connect />
        <GameModes />
        <Civilizations />
        <CTA />
      </main>
      <Footer />
    </>
  );
}
