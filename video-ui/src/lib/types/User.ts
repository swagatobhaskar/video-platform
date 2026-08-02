export type User = {
    id: string;
    email: string;
    username: string | null;
    role: 'admin' | 'user';
}