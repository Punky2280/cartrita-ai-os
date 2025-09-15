import type { NextApiRequest, NextApiResponse } from "next";
import { cartritaBio } from "@/utils/cartritaBio";

export default function handler(_req: NextApiRequest, res: NextApiResponse) {
  // Lightweight public bio endpoint for SSR or external tooling
  res.setHeader(
    "Cache-Control",
    "public, s-maxage=300, stale-while-revalidate=600",
  );
  res.status(200).json({ success: true, data: cartritaBio });
}
