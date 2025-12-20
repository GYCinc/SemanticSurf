export default {
  name: 'analysisCard',
  title: 'Active Focus Card',
  type: 'document',
  fields: [
    // 1. The Content (Study Material)
    {
      name: 'category',
      title: 'Category',
      type: 'string',
      options: {
        list: [
          { title: 'Vocabulary Gap', value: 'VOCAB_GAP' },
          { title: 'Grammar Error', value: 'GRAMMAR_ERR' },
          { title: 'Recast', value: 'RECAST' },
          { title: 'Avoidance', value: 'AVOIDANCE' },
          { title: 'Pronunciation', value: 'PRONUNCIATION' }
        ]
      }
    },
    { name: 'detectedTrigger', type: 'string', title: 'Student Said' },
    { name: 'suggestedCorrection', type: 'string', title: 'Correction' },
    { name: 'explanation', type: 'text', title: 'Why?' },

    // 2. The "Bridge" (Link to Supabase)
    {
      name: 'sourceReference',
      title: 'Source Context',
      type: 'object',
      fields: [
        { 
          type: 'string', 
        },
        { 
          name: 'timestamp', 
          type: 'number', 
          description: 'Time in seconds where this happened' 
        }
      ]
    }
  ]
}

