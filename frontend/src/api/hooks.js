import { useMutation, useQuery } from "@tanstack/react-query";

import client from "./client";
import { useWorkspace } from "../context/WorkspaceContext";

const get = (url, params) => () => client.get(url, { params }).then((r) => r.data);

// 30s polling gives the dashboard its "live" feel without websockets.
const live = { refetchInterval: 30000 };

function useScopedQuery(key, url, params, options = {}) {
  const { facilityId } = useWorkspace();
  const scoped = { ...params, facility_id: facilityId || undefined };
  return useQuery({ queryKey: [key, scoped], queryFn: get(url, scoped), ...options });
}

export const useSummary = () => useScopedQuery("summary", "/emissions/summary", {}, live);

export const useLatest = (params) =>
  useScopedQuery("latest", "/emissions/latest", params, live);

export const useTimeseries = (params) =>
  useScopedQuery("timeseries", "/emissions/timeseries", params, live);

export const useAnomalies = (params) =>
  useScopedQuery("anomalies", "/anomalies", params);

export const useFacilities = () =>
  useQuery({ queryKey: ["facilities"], queryFn: get("/facilities") });

export const useActivityDrafts = () =>
  useScopedQuery("activity-drafts", "/activity/drafts");

export const useActivity = () => useScopedQuery("scenario-records", "/activity");

export const useCreateFacility = () =>
  useMutation({
    mutationFn: async (payload) => {
      const { data } = await client.post("/facilities", payload);
      return data;
    },
  });

export const useCreateOCRDraft = () =>
  useMutation({
    mutationFn: async (file) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await client.post("/activity/ocr", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
  });

export const useCreateExcelDraft = () =>
  useMutation({
    mutationFn: async ({ file, facilityId }) => {
      const formData = new FormData();
      formData.append("file", file);
      if (facilityId) formData.append("facility_id", facilityId);
      const { data } = await client.post("/activity/excel", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
  });

export const useConfirmOCRDraft = () =>
  useMutation({
    mutationFn: async (draftId) => {
      const { data } = await client.post(`/activity/ocr/${draftId}/confirm`);
      return data;
    },
  });

export const useRejectOCRDraft = () =>
  useMutation({
    mutationFn: async (draftId) => {
      await client.delete(`/activity/ocr/${draftId}`);
    },
  });
