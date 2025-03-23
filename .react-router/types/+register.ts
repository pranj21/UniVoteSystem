import "react-router";

declare module "react-router" {
  interface Register {
    params: Params;
  }
}

type Params = {
  "/": {};
  "/voter": {};
  "/voter_register": {};
  "/candidate": {};
  "/candidate_register": {};
  "/voter_dashboard": {};
  "/candidate_dashboard": {};
  "/voter_profile": {};
  "/admin": {};
  "/admin_dashboard": {};
  "/auditor": {};
  "/auditor_dashboard": {};
};