
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	type MatcherParam<M> = M extends (param : string) => param is (infer U extends string) ? U : string;

	export interface AppTypes {
		RouteId(): "/" | "/credits" | "/dashboard" | "/discover" | "/docs" | "/keys" | "/license" | "/login" | "/my" | "/my/calls" | "/my/services" | "/privacy" | "/publish" | "/security" | "/service" | "/service/[id]" | "/terms";
		RouteParams(): {
			"/service/[id]": { id: string }
		};
		LayoutParams(): {
			"/": { id?: string | undefined };
			"/credits": Record<string, never>;
			"/dashboard": Record<string, never>;
			"/discover": Record<string, never>;
			"/docs": Record<string, never>;
			"/keys": Record<string, never>;
			"/license": Record<string, never>;
			"/login": Record<string, never>;
			"/my": Record<string, never>;
			"/my/calls": Record<string, never>;
			"/my/services": Record<string, never>;
			"/privacy": Record<string, never>;
			"/publish": Record<string, never>;
			"/security": Record<string, never>;
			"/service": { id?: string | undefined };
			"/service/[id]": { id: string };
			"/terms": Record<string, never>
		};
		Pathname(): "/" | "/credits" | "/dashboard" | "/discover" | "/docs" | "/keys" | "/license" | "/login" | "/my/calls" | "/my/services" | "/privacy" | "/publish" | "/security" | `/service/${string}` & {} | "/terms";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): string & {};
	}
}