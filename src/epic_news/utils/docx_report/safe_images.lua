-- Keep only images stored under the report output directory; replace any other
-- image (URL, file:// URI, path outside output/, `..` escape) by its alt text
-- before pandoc fetches it. Fragments are LLM output and must not make pandoc
-- read local files or contact the network.
--
-- The allowed root arrives as the `epic_image_root` metadata field and is
-- removed from the document so it never lands in the DOCX properties.

local root = nil

local function is_allowed(src)
  if root == nil or src:find("%.%.") or src:find("^%a[%w+.-]*:") then
    return false
  end
  if src:sub(1, 1) == "/" then
    return src:sub(1, #root + 1) == root .. "/"
  end
  return src:sub(1, 7) == "output/"
end

return {
  {
    Meta = function(meta)
      if meta.epic_image_root then
        root = pandoc.utils.stringify(meta.epic_image_root)
        meta.epic_image_root = nil
      end
      return meta
    end,
  },
  {
    Image = function(img)
      if is_allowed(img.src) then
        return img
      end
      return img.caption
    end,
  },
}
