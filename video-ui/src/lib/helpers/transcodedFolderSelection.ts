/**
 * Turns whatever the user picked/dropped into:
 *   - the parent folder name ("my-video")
 *   - the parsed probe_result.json metadata
 *   - the exact list of files to upload (everything under <parent>/dash/)
 *
 * Expected layout:  my-video/dash/...   and   my-video/probe_result.json
 */
 
export type FolderEntry = { file: File; relativePath: string };
 
export type ProbeResult = {
    width: number;
    height: number;
    codec: string;
    fps: number;
    bitrate: number;
    duration_seconds: number;
};
 
export type PreparedFolder = {
    folderName: string;
    probe: ProbeResult;
    uploadEntries: FolderEntry[];
    /** Files that were selected but are neither probe_result.json nor under dash/ (e.g. .DS_Store). */
    ignored: string[];
};
 
// ---------- 1. Getting entries from the two input methods ----------
 
/** <input type="file" webkitdirectory> -- paths come for free via webkitRelativePath. */
export function entriesFromInput(files: FileList | File[]): FolderEntry[] {
    return Array.from(files).map(file => ({
        file,
        relativePath: file.webkitRelativePath || file.name,
    }));
}
 
/** readEntries() hands back at most ~100 entries per call, so keep calling until it returns []. */
function readAllEntries(reader: FileSystemDirectoryReader): Promise<FileSystemEntry[]> {
    return new Promise((resolve, reject) => {
        const all: FileSystemEntry[] = [];
        const readBatch = () =>
            reader.readEntries(batch => {
                if (batch.length === 0) return resolve(all);
                all.push(...batch);
                readBatch();
            }, reject);
        readBatch();
    });
}
 
async function walk(entry: FileSystemEntry, out: FolderEntry[]): Promise<void> {
    if (entry.isFile) {
        const file = await new Promise<File>((resolve, reject) =>
            (entry as FileSystemFileEntry).file(resolve, reject),
        );
        // fullPath is "/my-video/dash/x.m4s" -- strip the leading slash to match webkitRelativePath.
        out.push({ file, relativePath: entry.fullPath.replace(/^\//, "") });
    } else if (entry.isDirectory) {
        const children = await readAllEntries((entry as FileSystemDirectoryEntry).createReader());
        await Promise.all(children.map(child => walk(child, out)));
    }
}
 
/**
 * Drag-and-drop. IMPORTANT: call this directly inside the `drop` handler.
 * DataTransferItems are invalidated as soon as the handler yields, so the
 * webkitGetAsEntry() calls below must run synchronously, before any `await`.
 */
export async function entriesFromDrop(dataTransfer: DataTransfer): Promise<FolderEntry[]> {
    const roots = Array.from(dataTransfer.items)
        .map(item => item.webkitGetAsEntry())
        .filter((entry): entry is FileSystemEntry => entry !== null);
 
    const out: FolderEntry[] = [];
    await Promise.all(roots.map(root => walk(root, out)));
    return out.sort((a, b) => a.relativePath.localeCompare(b.relativePath));
}
 
// ---------- 2. probe_result.json parsing ----------
 
function toNumber(value: unknown, label: string): number {
    const n = typeof value === "string" ? Number(value) : value;
    if (typeof n !== "number" || !Number.isFinite(n)) {
        throw new Error(`probe_result.json has an invalid "${label}" value.`);
    }
    return n;
}
 
// ffprobe often reports frame rate as a fraction, e.g. "30000/1001".
function parseFps(value: unknown): number {
    if (typeof value === "string" && value.includes("/")) {
        const [num, den] = value.split("/").map(Number);
        if (den) return num / den;
    }
    return toNumber(value, "fps");
}
 
function parseProbe(raw: Record<string, unknown>): ProbeResult {
    const codec = typeof raw.codec === "string" ? raw.codec.trim() : "";
    if (!codec) throw new Error('probe_result.json has an invalid "codec" value.');
 
    return {
        width: Math.round(toNumber(raw.width, "width")),
        height: Math.round(toNumber(raw.height, "height")),
        codec,
        fps: Number(parseFps(raw.fps).toFixed(3)),
        // NOTE: Video.bitrate is documented as kbps. If your probe file stores bits/sec
        // (ffprobe's default), divide by 1000 here.
        bitrate: Math.round(toNumber(raw.bitrate, "bitrate")),
        duration_seconds: toNumber(raw.duration, "duration"),
    };
}
 
// ---------- 3. Putting it together ----------
 
export async function prepareTranscodedFolder(
    entries: FolderEntry[],
    options: { fallbackName?: string } = {},
): Promise<PreparedFolder> {
    // Normal case: "my-video/dash/..." -> parent is the first path segment.
    let folderName = entries
        .find(e => e.relativePath.split("/")[1] === "dash")
        ?.relativePath.split("/")[0];
    let normalized = entries;
 
    if (!folderName) {
        // Only dash/ itself was selected/dropped. The browser doesn't expose its parent.
        if (!entries.some(e => e.relativePath.startsWith("dash/"))) {
            throw new Error("No dash/ folder found. Select the folder that contains dash/ and probe_result.json.");
        }
        if (!options.fallbackName) {
            throw new Error(
                "Only dash/ was selected, so the parent folder name and probe_result.json are unavailable. " +
                    "Select the parent folder instead.",
            );
        }
        folderName = options.fallbackName;
        const prefix = folderName;
        // Re-root so paths satisfy the backend's "<name>/dash/<file>" validation.
        normalized = entries.map(e => ({ ...e, relativePath: `${prefix}/${e.relativePath}` }));
    }
 
    const probeEntry = normalized.find(e => e.relativePath === `${folderName}/probe_result.json`);
    if (!probeEntry) {
        throw new Error("probe_result.json was not found next to the dash/ folder.");
    }
 
    let probe: ProbeResult;
    try {
        probe = parseProbe(JSON.parse(await probeEntry.file.text()));
    } catch (error) {
        if (error instanceof SyntaxError) {
            // cause: error preserves the original SyntaxError for debugging.
            // Your custom error message remains user-friendly.
            // The original error is accessible through newError.cause.
            // Rethrowing error in the final line preserves all other errors unchanged.
            throw new Error("probe_result.json is not valid JSON.", {cause: error})
        };
        throw error;
    }
 
    const uploadEntries = normalized.filter(e => e.relativePath.startsWith(`${folderName}/dash/`));
    const uploadSet = new Set(uploadEntries);
    const ignored = normalized
        .filter(e => e !== probeEntry && !uploadSet.has(e))
        .map(e => e.relativePath);
 
    return { folderName, probe, uploadEntries, ignored };
}
 