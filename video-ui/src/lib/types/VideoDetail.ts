// export type VideoDetail = {
//     id: string;
//     title: string;
//     slug: string | null;
//     publication_status: string;
//     created_at: Date;
//     updated_at: Date;
//     object_key: string | null;
//     like_count: number;
//     dislike_count: number;
//     thumbnail_alt_text: string | null;
//     thumbnail_object_key: string | null;
// }

export type Language =
	| "hindi"
	| "bengali";

export type VideoPublicationStatus =
	| "draft"
	| "published"
	| "archived";

export type VideoDetail = {
	id: string;

	object_key: string | null;

	category_id: string | null;
	series_id: string | null;

	title: string | null;
	slug: string | null;
	description: string | null;

	created_at: string;
	updated_at: string;
	published_at: string | null;

	episode_number: number | null;

	thumbnail_alt_text: string | null;
	thumbnail_object_storage_prefix: string | null;

	language: Language | null;

	bitrate: number | null;
	codec: string | null;

	view_count: number;
	like_count: number;
	dislike_count: number;

	width: number | null;
	height: number | null;
	fps: number | null;
	duration_seconds: number | null;

	publication_status: VideoPublicationStatus;

	meta_title: string | null;
	seo_summary_en: string | null;
	meta_description: string | null;

	keywords: (string | null)[];
	seo_tags: (string | null)[];
	search_intent: string | null;
	focus_keyword: string | null;
	secondary_keywords: (string | null)[];

	// computed fields
	thumbnail_url: string | null;
	hls_url: string | null;
	dash_url: string | null;
};
