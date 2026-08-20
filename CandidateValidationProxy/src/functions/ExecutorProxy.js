const { app } = require('@azure/functions');

const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || "*";

function getConfig() {
    return {
        executorUrl: process.env.IGENTIC_EXECUTOR_URL,
        appId: process.env.IGENTIC_APP_ID,
        apiKey: process.env.IGENTIC_API_KEY,
        bearerToken: process.env.IGENTIC_BEARER_TOKEN,
        username: process.env.IGENTIC_USERNAME,
        streamingEnabled: process.env.STREAMING_ENABLED === 'true',
    };
}

function corsHeaders(contentType = "application/json") {
    return {
        "Content-Type": contentType,
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers":
            "Content-Type, Authorization, x-api-key, x-app-id, x-username, x-session-id, x-execution-id, x-connection-id",
    };
}

function buildAuthHeaders(body) {
    const cfg = getConfig();

    const headers = {
        Authorization: `Bearer ${cfg.bearerToken}`,
        "x-api-key": cfg.apiKey,
        "x-app-id": cfg.appId,
        "x-username": cfg.username,
        "Content-Type": "application/json",
    };

    if (body.session_id) headers["x-session-id"] = body.session_id;
    if (body.execution_id) headers["x-execution-id"] = body.execution_id;
    if (body.connection_id) headers["x-connection-id"] = body.connection_id;

    return headers;
}

app.http("ExecutorProxy", {
    methods: ["POST", "OPTIONS"],
    authLevel: "anonymous",
    route: "executorproxy",

    handler: async (request, context) => {

        if (request.method === "OPTIONS") {
            return {
                status: 200,
                headers: corsHeaders(),
            };
        }

        try {

            const cfg = getConfig();

            if (!cfg.executorUrl) {
                throw new Error("IGENTIC_EXECUTOR_URL is not configured");
            }

            const body = await request.json();

            const headers = buildAuthHeaders(body);

            if (cfg.streamingEnabled) {

                const upstream = await fetch(cfg.executorUrl, {
                    method: "POST",
                    headers: {
                        ...headers,
                        Accept: "text/event-stream",
                    },
                    body: JSON.stringify(body),
                });

                const contentType =
                    upstream.headers.get("content-type") || "";

                if (contentType.includes("text/event-stream")) {

                    return {
                        status: upstream.status,
                        headers: {
                            ...corsHeaders("text/event-stream"),
                            "Cache-Control": "no-cache",
                            Connection: "keep-alive",
                            "x-session-id": body.session_id || "",
                        },
                        body: upstream.body,
                    };
                }

                const text = await upstream.text();

                return {
                    status: upstream.status,
                    headers: corsHeaders(),
                    body: text,
                };
            }

            const upstream = await fetch(cfg.executorUrl, {
                method: "POST",
                headers,
                body: JSON.stringify(body),
            });

            const text = await upstream.text();

            return {
                status: upstream.status,
                headers: corsHeaders(),
                body: text,
            };

        } catch (err) {

            context.error(err);

            return {
                status: 500,
                headers: corsHeaders(),
                body: JSON.stringify({
                    success: false,
                    message: err.message || "Internal proxy error",
                }),
            };
        }
    },
});