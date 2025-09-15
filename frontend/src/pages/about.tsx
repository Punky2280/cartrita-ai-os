import Head from "next/head";
import Link from "next/link";
import type { GetServerSideProps } from "next";
import { motion } from "framer-motion";
import { cartritaBio } from "@/utils/cartritaBio";
import SeoHead from "@/components/SeoHead";
import type { CartritaBio } from "@/types/CartritaBio";

type Props = {
  initialBio?: CartritaBio;
};

export default function AboutPage({ initialBio }: Props) {
  const bio = initialBio ?? cartritaBio;
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL;
  const pageUrl = siteUrl ? `${siteUrl.replace(/\/$/, "")}/about` : undefined;
  const title = `About • ${bio.name}`;
  const description = `${bio.name} — ${bio.title} from ${bio.origin}. ${bio.mission}`;
  return (
    <>
      <SeoHead
        title={title}
        description={description}
        url={pageUrl}
        image="/og-about.svg"
        imageType="image/svg+xml"
      />
      <main className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-925 to-gray-900 text-gray-100">
        <section className="mx-auto max-w-5xl px-6 py-12">
          <motion.h1
            initial={{ y: 12, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.4 }}
            className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-yellow-300 via-pink-400 to-purple-400 bg-clip-text text-transparent"
          >
            {bio.name}: {bio.title}
          </motion.h1>
          <p className="mt-4 text-lg text-gray-300">
            {bio.origin} • {bio.heritage} • {bio.location}
          </p>
          <p className="mt-6 text-gray-300 leading-relaxed max-w-3xl">
            {bio.mission}
          </p>

          <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="rounded-xl border border-white/10 bg-white/5 p-5">
              <h2 className="font-semibold text-yellow-300">Values</h2>
              <ul className="mt-3 space-y-2 list-disc list-inside text-gray-200">
                {bio.values.map((v) => (
                  <li key={v}>{v}</li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-5">
              <h2 className="font-semibold text-pink-300">Personality</h2>
              <ul className="mt-3 space-y-2 list-disc list-inside text-gray-200">
                {bio.personality.map((v) => (
                  <li key={v}>{v}</li>
                ))}
              </ul>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-5">
              <h2 className="font-semibold text-purple-300">Capabilities</h2>
              <ul className="mt-3 space-y-2 list-disc list-inside text-gray-200">
                {bio.capabilities.map((v) => (
                  <li key={v}>{v}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-10 rounded-xl border border-white/10 bg-white/5 p-5">
            <h2 className="font-semibold">Agents</h2>
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {bio.agents.map((a) => (
                <div
                  key={a.id}
                  className="rounded-lg bg-black/30 border border-white/10 p-4"
                >
                  <div className="text-sm text-gray-400">{a.id}</div>
                  <div className="font-semibold">{a.name}</div>
                  <div className="text-sm text-gray-300">{a.role}</div>
                  <div className="text-xs text-gray-400 mt-1">
                    Model: {a.model}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-10 space-y-8">
            {bio.story.map((s) => (
              <article
                key={s.id}
                className="rounded-xl border border-white/10 bg-white/5 p-6"
              >
                <h3 className="text-xl md:text-2xl font-bold text-white/95">
                  {s.title}
                </h3>
                <p className="mt-2 text-sm text-gray-400">{s.summary}</p>
                <p className="mt-4 text-gray-200 leading-relaxed">
                  {s.content}
                </p>
              </article>
            ))}
          </div>

          <figure className="mt-10">
            <blockquote className="text-lg italic text-gray-200">
              {bio.quotes[0]}
            </blockquote>
            <figcaption className="mt-2 text-sm text-gray-400">
              — {bio.name}
            </figcaption>
          </figure>

          <div className="mt-12">
            <Link
              href="/"
              className="inline-block rounded-lg bg-gradient-to-r from-yellow-400 to-pink-500 px-5 py-2.5 font-semibold text-black shadow hover:opacity-95 focus:outline-none focus:ring-2 focus:ring-yellow-300"
            >
              Back to Home
            </Link>
          </div>
        </section>
      </main>
    </>
  );
}

export const getServerSideProps: GetServerSideProps<Props> = async () => {
  const base = (
    process.env.BACKEND_BASE_URL ||
    process.env.NEXT_PUBLIC_BACKEND_BASE_URL ||
    "http://localhost:8000"
  ).replace(/\/$/, "");
  const apiKey = process.env.CARTRITA_API_KEY || "dev-api-key-2025";

  try {
    const res = await fetch(
      `${base}/api/bio?api_key=${encodeURIComponent(apiKey)}`,
      {
        method: "GET",
        headers: { Accept: "application/json" },
      },
    );

    if (res.ok) {
      const json = await res.json();
      const data = json?.data as CartritaBio | undefined;
      if (data && typeof data === "object" && Array.isArray(data.values)) {
        return { props: { initialBio: data } };
      }
    }
  } catch {
    // fall through to local fallback
  }

  return { props: { initialBio: cartritaBio } };
};
