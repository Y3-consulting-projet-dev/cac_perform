import axios from 'axios' // ton axios déjà configuré

export const getGrouping = (type = null) => {
  const params = type ? { type } : {};
  return axios.get("/grouping/", { params });
};
