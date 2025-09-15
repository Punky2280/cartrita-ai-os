import Head from "next/head";

type Props = {
  title: string;
  description: string;
  url?: string;
  image?: string;
  imageType?: string;
};

const DEFAULTS = {
  siteName: "Cartrita AI OS",
  twitterCard: "summary",
};

export function SeoHead({ title, description, url, image, imageType }: Props) {
  return (
    <Head>
      <title>{title}</title>
      <meta name="description" content={description} />

      {/* Open Graph */}
      <meta property="og:site_name" content={DEFAULTS.siteName} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content="website" />
      {url ? <meta property="og:url" content={url} /> : null}
      {image ? <meta property="og:image" content={image} /> : null}
      {imageType ? <meta property="og:image:type" content={imageType} /> : null}

      {/* Twitter */}
      <meta name="twitter:card" content={DEFAULTS.twitterCard} />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      {image ? <meta name="twitter:image" content={image} /> : null}

      {/* Canonical */}
      {url ? <link rel="canonical" href={url} /> : null}
    </Head>
  );
}

export default SeoHead;
