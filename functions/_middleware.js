export const onRequest = ({ request, next }) => {
  const url = new URL(request.url);

  if (url.hostname.endsWith("pages.dev")) {
    url.hostname = "79king.ai";
    return Response.redirect(url.toString(), 301);
  }


  return next();
};
