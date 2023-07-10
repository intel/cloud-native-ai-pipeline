
export interface Pipeline {
  pipeline_id: string;
  model_name: string;
  stream_name: string;
  input_fps: number;
  infer_fps: number;
};
