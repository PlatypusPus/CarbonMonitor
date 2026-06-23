import { useQuery } from "@tanstack/react-query";

import client from "./client";

const get = (url, params) => () => client.get(url, { params }).then((r) => r.data);

// 30s polling gives the dashboard its "live" feel without websockets.
const live = { refetchInterval: 30000 };

export const useSummary = () =>
  useQuery({ queryKey: ["summary"], queryFn: get("/emissions/summary"), ...live });

export const useLatest = (params) =>
  useQuery({ queryKey: ["latest", params], queryFn: get("/emissions/latest", params), ...live });

export const useTimeseries = (params) =>
  useQuery({ queryKey: ["timeseries", params], queryFn: get("/emissions/timeseries", params), ...live });

export const useAnomalies = (params) =>
  useQuery({ queryKey: ["anomalies", params], queryFn: get("/anomalies", params) });
