import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
    index("routes/home.tsx"),
    route("voter", "routes/voter.tsx"),
    route("voter_register", "routes/voter_register.tsx"),
    route("candidate", "routes/candidate.tsx"),
    route("candidate_register", "routes/candidate_register.tsx"),
    route("voter_dashboard", "routes/voter_dashboard.tsx"),
    route("candidate_dashboard", "routes/candidate_dashboard.tsx"),
    route("/voter_profile","routes/voter_profile.tsx"),
    route("/admin","routes/admin.tsx"),
    route("/admin_dashboard","routes/admin_dashboard.tsx"),
    route("/auditor","routes/auditor.tsx"),
    route("/auditor_dashboard","routes/auditor_dashboard.tsx")


] satisfies RouteConfig;
