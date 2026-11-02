import { type VideoTranscript } from "./VideoTranscript";
import { type Series } from "./Series";
import { type Category } from "./Category";

export interface VideoView {
	id: number | string;
	title: string;
	slug: string;
	language?: string | null;
	description?: string | null;
	meta_title?: string | null;
	meta_description?: string | null;
	thumbnail_object_key?: string | null;
	thumbnail_alt_text?: string | null;
	dash_manifest_key?: string | null;
	hls_manifest_key?: string | null;
	published_at?: string | null;
	duration_seconds?: number | null;
	view_count: number;
	like_count: number;
	dislike_count: number;
	category?: Category | null;
	series?: Series | null;
	episode_number?: number | null;
	video_transcripts?: VideoTranscript[] | null;
}
