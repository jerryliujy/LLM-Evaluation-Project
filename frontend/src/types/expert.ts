// Expert related types
export interface Expert {
  id: number;
  name: string;
  email: string;
  is_deleted: boolean;
  created_at?: string;
}

export interface ExpertCreate {
  name: string;
  email: string;
  password: string;
}

export interface ExpertLogin {
  email: string;
  password: string;
}

export interface ExpertLoginResponse {
  expert: Expert;
  access_token?: string;
  token_type?: string;
}
