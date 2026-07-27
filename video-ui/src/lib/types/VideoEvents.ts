type JsonValue =
	| string
	| number
	| boolean
	| null
	| JsonValue[]
	| { [key: string]: JsonValue };

export type VideoEvent = {
	id: string;
	transcode_task_id: string | null;
	video_id: string;
	event_type: string;
	payload: JsonValue | null;
	created_at: string;
	updated_at: string;
};