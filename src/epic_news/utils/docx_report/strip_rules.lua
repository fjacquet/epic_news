-- LLM fragments separate paragraphs with `---` / `***`, which pandoc turns into
-- horizontal rules in the DOCX. Section headings already structure the report,
-- so drop every rule.
return {
  {
    HorizontalRule = function()
      return {}
    end,
  },
}
