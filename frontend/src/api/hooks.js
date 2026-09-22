import { useMutation, useQuery } from "@tanstack/react-query";

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

export const useCrossVerify = (params) =>
  useQuery({ queryKey: ["crossverify", params], queryFn: get("/emissions/crossverify", params) });

export const useFacilities = () =>
  useQuery({ queryKey: ["facilities"], queryFn: get("/facilities") });

export const useActivityDrafts = () =>
  useQuery({ queryKey: ["activity-drafts"], queryFn: get("/activity") });

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
