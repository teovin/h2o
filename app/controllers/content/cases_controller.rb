require 'net/http'
require 'uri'

class Content::CasesController < ApplicationController
  # create a temporary resource to display the case
  layout 'casebooks'
  def show
    @case = Case.find(params[:case_id])

    unless @case.try :public
      flash[:notice] = "You are not authorized to access this page."
      redirect_to :root and return
    end

    @resource = Content::Resource.new resource: @case
    @content = @resource
    render 'content/resources/show'
  end
end
