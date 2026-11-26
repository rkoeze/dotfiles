import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

function isOpenAI({ model }: ExtensionContext) {
  return model?.provider === "openai" || model?.provider === "openai-codex";
}

export default function fast(pi: ExtensionAPI) {
  let enabled = false;

  pi.registerCommand("fast", {
    description: "Toggle OpenAI Fast mode (higher usage): /fast [on|off]",
    handler: async (args, ctx) => {
      if (!isOpenAI(ctx)) {
        if (ctx.hasUI) ctx.ui.notify("Select an OpenAI or Codex model to use /fast.", "warning");
        return;
      }
      const arg = args.trim().toLowerCase();
      if (arg !== "" && arg !== "on" && arg !== "off") {
        if (ctx.hasUI) ctx.ui.notify("Usage: /fast [on|off]", "warning");
        return;
      }
      enabled = arg === "" ? !enabled : arg === "on";
      if (ctx.hasUI) ctx.ui.notify(`${ctx.model?.provider} fast mode ${enabled ? "on" : "off"}.`, "info");
    },
  });

  pi.on("before_provider_request", ({ payload }, ctx) => {
    if (!enabled || !isOpenAI(ctx)) return;
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) return;
    // OpenAI calls the Fast service tier "priority" on the wire.
    return { ...payload, service_tier: "priority" };
  });
}
