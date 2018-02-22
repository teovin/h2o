class MergeDraftIntoPublishedCasebook
  attr_reader :draft, :published, :revisions

  def self.perform(draft, published)
    new(draft, published).perform
  end

  def initialize(draft, published)
    @draft = draft
    @published = published
    @revisions = UnpublishedRevision.where(casebook_id: @draft.id)
  end

  def perform
    begin
      remove_deleted_contents
      add_new_contents
      reflow_published_ordinals
      merge_in_unpublished_revisions
      new_and_updated_annotations
      deleted_annotations
      # content_collaborators
      draft.destroy

      {success: true, casebook: published}
    rescue Exception => e
      Notifier.merge_failed(draft.owner, draft, published, e, e.backtrace).deliver
      Rails.logger.warn "Casebook merge failure: #{e.inspect}"
      {success: false, casebook: draft}
    end
  end

  def remove_deleted_contents
    draft_contents_copy_of_ids = draft.contents.pluck(:copy_of_id).compact.uniq

    published.contents.each do |published_content|
      if draft_contents_copy_of_ids.exclude? published_content.id
        published_content.destroy
      end
    end
  end

  def reflow_published_ordinals
    previously_created_contents.each do |content|
      parent_content = content.copy_of
      if content.ordinals != parent_content.ordinals
        parent_content.update(ordinals: content.ordinals)
      end
    end
  end

  def add_new_contents
    if new_contents.present?
      new_contents.each do |content|
        new_content = content.dup
        new_content.update(casebook_id: published.id)
      end
    end
  end

  def merge_in_unpublished_revisions
    resource_revisions.each do |revision|
      resource = Content::Node.find(revision.node_parent_id)
      if casebook_detail?(revision.field)
        resource.update("#{revision.field}": revision.value)
      else
        resource.resource.update("#{revision.field}": revision.value)
      end
      revision.destroy
    end
  end

  def new_and_updated_annotations
    new_or_updated_annotations.each do |annotation|
      resource = annotation.resource.copy_of

      if annotating_new_resource?(annotation)
        resource = Content::Resource.where(copy_of_id: annotation.resource_id).last
      elsif annotation.exists_in_published_casebook?
        old_annotation = resource.annotations.where(start_p: annotation.start_p, end_p: annotation.end_p, 
          start_offset: annotation.start_offset, end_offset: annotation.end_offset).first
        old_annotation.destroy
      end

      annotation.update(resource_id: resource.id)
    end
  end

  def deleted_annotations
    revisions.where(field: "deleted_annotation").each do |revision|
      Content::Annotation.find(revision.value.to_i).destroy
    end
  end

  def content_collaborators
    #if a user is deleted, added or role is changed
    #multiple collaborator functionality doesn't exist yet so
    #holding this method for the future
  end

  private

  def previously_created_contents
    draft.contents.where.not(copy_of_id: nil)
  end

  def new_contents
    draft.contents.where(copy_of_id: nil)
  end

  def resource_revisions
    revisions.where.not(field: "deleted_annotation")
  end

  def casebook_detail?(field)
    %w(url content).exclude? field
  end

  def draft_resource_ids
    draft.resources.pluck(:id)
  end

  def new_or_updated_annotations
    Content::Annotation.where(resource_id: draft_resource_ids).where("updated_at > ?", draft.created_at + 1.minute)
  end

  def annotating_new_resource?(annotation)
    ! annotation.resource.exists_in_published_casebook?
  end
end