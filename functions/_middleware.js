export const onRequest = ({ request, next }) => {
  const url = new URL(request.url);

  if (url.hostname.endsWith("pages.dev")) {
    const targetUrl = `https://79king.ai${url.pathname}${url.search}`;
    return Response.redirect(targetUrl, 301);
  }

  return next();
};
